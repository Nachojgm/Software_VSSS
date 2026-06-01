import cv2


def draw_overlay(frame, state, targets=None, homography_ready=False):
    if frame is None:
        return None

    output = frame.copy()
    if state.ball is not None:
        center = (int(state.ball.x_px), int(state.ball.y_px))
        cv2.circle(output, center, int(max(8, state.ball.radius_px)), (0, 140, 255), 2)
        cv2.putText(output, "ball", (center[0] + 8, center[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 2)

    for robot in state.robots:
        center = (int(robot.x_px), int(robot.y_px))
        cv2.circle(output, center, 18, (255, 80, 40), 2)
        cv2.putText(
            output,
            f"R{robot.robot_id}/M{robot.marker_id}",
            (center[0] + 10, center[1] + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 80, 40),
            2,
        )

    label = "calibrada" if homography_ready else "pixeles"
    cv2.putText(output, f"Cancha: {label}", (14, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (250, 250, 250), 2)
    return output
