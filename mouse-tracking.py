from pynput.mouse import Controller as MouseController

import cv2
import numpy as np
import ctypes
user32 = ctypes.windll.user32

algo_width = 1280
algo_height = 720
deadzone = 100
preview_ratio = 0.25
marker_lower = (108, 79, 0)
marker_upper = (124, 255, 255)


half_deadzone = deadzone // 2

algo_width += deadzone
algo_height += deadzone

preview_width = int(algo_width * preview_ratio)
preview_height = int(algo_height * preview_ratio)


WINDOW_REGION_OF_INTEREST = 'Select Region of Interest'
WINDOW_PREVIEW = 'Foot Mouse Preview (q to stop)'


def get_region_of_interest(source, flip_code):
    """
    Prompt the user to select their region of interest.
    :return: The selected region of interest as a numpy matrix of points in the order tl, tr, br, bl.
    """
    points = []
    done = False
    width, height = 0, 0

    def on_click(evt, x, y, *_):
        nonlocal done

        if flip_code in (0, -1):
            # Flip vertical
            y = height - y

        if flip_code in (1, -1):
            # Flip horizontal
            x = width - x

        if evt == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 4:
                points.append((x, y))
            else:
                done = True

        if evt == cv2.EVENT_RBUTTONDOWN:
            if len(points) > 0:
                points.pop()

    cv2.namedWindow(WINDOW_REGION_OF_INTEREST)
    cv2.setMouseCallback(WINDOW_REGION_OF_INTEREST, on_click)
    while not done:
        _, frame = source.read()
        height, width, _ = frame.shape

        # Draw the connecting lines
        for a, b in zip(points, points[1:]):
            cv2.line(frame, a, b, (0, 127, 255), 2)
        if len(points) == 4:
            cv2.line(frame, points[0], points[-1], (0, 127, 255), 2)

        # Draw the points
        for point in points:
            cv2.circle(frame, point, 7, (0, 127, 255), -1)

        if type(flip_code) == int:
            frame = cv2.flip(frame, flip_code)

        cv2.imshow(WINDOW_REGION_OF_INTEREST, frame)
        cv2.waitKey(1)

    cv2.destroyWindow(WINDOW_REGION_OF_INTEREST)

    points = np.array(points)

    # Reorder the points so that top-left is the first and they are clockwise.
    region = np.zeros((4, 2), dtype="float32")
    s = points.sum(axis=1)
    region[0] = points[np.argmin(s)]
    region[2] = points[np.argmax(s)]
    diff = np.diff(points, axis=1)
    region[1] = points[np.argmin(diff)]
    region[3] = points[np.argmax(diff)]

    return region


def solve_perspective(region, flip_code):
    """
    Create a perspective transform matrix to correct for the skewed rectangles from depth. Also flips the image if
    needed using the same matrix.
    :param region: Original region of interest's coordinates
    :param flip_code: The direction to flip
    :return: Transformation matrix
    """
    dst = np.array([
        [0, 0],
        [algo_width, 0],
        [algo_width, algo_height],
        [0, algo_height]
    ], dtype="float32")

    if flip_code in (0, -1):
        # Flip vertical
        dst[[0, 3]] = dst[[3, 0]]
        dst[[1, 2]] = dst[[2, 1]]

    if flip_code in (1, -1):
        # Flip horizontal
        dst[[0, 1]] = dst[[1, 0]]
        dst[[2, 3]] = dst[[3, 2]]

    return cv2.getPerspectiveTransform(region, dst)


def draw_deadzone(img):
    dz = img.copy()
    w = algo_width - half_deadzone
    h = algo_height - half_deadzone

    cv2.line(dz, (0, half_deadzone), (algo_width, half_deadzone), (0, 0, 0), deadzone)
    cv2.line(dz, (0, h), (algo_width, h), (0, 0, 0), deadzone)
    cv2.line(dz, (half_deadzone, 0), (half_deadzone, algo_height), (0, 0, 0), deadzone)
    cv2.line(dz, (w, 0), (w, algo_height), (0, 0, 0), deadzone)

    cv2.addWeighted(dz, 0.5, img, 0.5, 0, img)

    return img


def track_and_control_mouse(source, perspective_t):
    mouse = MouseController()

    while True:
        _, frame = source.read()
        warped = cv2.warpPerspective(frame, perspective_t, (algo_width, algo_height))

        hsv = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, marker_lower, marker_upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=4)

        contours, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contour_list = []
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            area = cv2.contourArea(contour)
            if (len(approx) > 8) & (area > 25):
                contour_list.append(contour)

        warped_with_deadzone = draw_deadzone(warped.copy())
        preview = cv2.resize(warped_with_deadzone, (preview_width, preview_height), interpolation=cv2.INTER_AREA)

        if len(contour_list):
            c = contour_list[0]
            m = cv2.moments(c)
            c_x = int(m["m10"] / m["m00"])
            c_y = int(m["m01"] / m["m00"])

            cv2.circle(preview, (int(c_x * preview_ratio), int(c_y * preview_ratio)), 15, (0, 127, 255), 2)

            ratio_x = min(1, max(c_x - deadzone, 0) / (algo_width - deadzone * 2))
            ratio_y = min(1, max(c_y - deadzone, 0) / (algo_height - deadzone * 2))

            mouse_x = ratio_x * user32.GetSystemMetrics(0)
            mouse_y = ratio_y * user32.GetSystemMetrics(1)

            mouse.position = (mouse_x, mouse_y)

        cv2.imshow(WINDOW_PREVIEW, preview)
        if cv2.waitKey(1) == ord('q'):
            break


def main():
    capture_source = int(input('Capture Source ID? '))
    flip_x = input('Flip horizontal? [y/N] ').lower() == 'y'
    flip_y = input('Flip vertical? [y/N] ').lower() == 'y'

    flip_code = [None, 1, 0, -1][flip_x + flip_y * 2]

    source = cv2.VideoCapture(capture_source, cv2.CAP_DSHOW)
    source.set(cv2.CAP_PROP_FPS, 60)
    source.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    source.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not source.isOpened():
        print("Couldn't open camera!")
        exit(1)

    roi = get_region_of_interest(source, flip_code)
    perspective_t = solve_perspective(roi, flip_code)
    track_and_control_mouse(source, perspective_t)


if __name__ == '__main__':
    main()
