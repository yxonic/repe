from .app import get_app


def main(args=None):
    """``fret`` script cli entry point.

    Args:
        args (list): command line arguments. If None, get args from
                     :data:`sys.argv` (default: ``None``)
    """
    return get_app().main(args)


if __name__ == '__main__':
    main()
