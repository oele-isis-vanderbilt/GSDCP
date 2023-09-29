import cv2


def stream_droidcam(ip, port, force_suffix=None):
    """Stream DroidCam frames."""
    addr = f"http://{ip}:{port}/video"
    if force_suffix is not None:
        addr += force_suffix

    cap = cv2.VideoCapture(addr)

    while True:
        ret, frame = cap.read()

        cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

    parser = ArgumentParser(
        description="Stream DroidCam frames.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--ip", type=str, required=True, help="IP address of the phone."
    )
    parser.add_argument(
        "--port", type=int, default=4747, help="Port of the phone."
    )
    parser.add_argument(
        "--force-suffix",
        type=str,
        default="/force/1920x1080",
        help="Force suffix for the phone.",
    )

    args = parser.parse_args()

    stream_droidcam(args.ip, args.port, args.force_suffix)
