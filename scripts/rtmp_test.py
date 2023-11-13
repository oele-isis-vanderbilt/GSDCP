import cv2


def stream_rtmp_frames(url):
    """Stream DroidCam frames."""
    addr = f"rtmp://{url}"
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
        description="Stream RTMP frames.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--url", "-u", type=str, required=True, help="URL of the remote stream."
    )

    args = parser.parse_args()

    stream_rtmp_frames(args.url)
