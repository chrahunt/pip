from pip._internal.utils.setuptools_build import make_setuptools_shim_args


class SetuptoolsArgsProvider(object):
    def __init__(self, isolated):
        super(SetuptoolsArgsProvider, self).__init__()
        self._isolated = isolated

    def install_args(
        self,
        setup_py_path,
        global_options,
        install_options,
        scheme,
        root,
        pycompile,
        record_filename,
    ):
        prefix = scheme["prefix"]
        headers = scheme["headers"]

        args = make_setuptools_shim_args(
            setup_py_path,
            global_options=global_options,
            no_user_config=self._isolated,
            unbuffered_output=True,
        )
        args.extend(["install", "--record", record_filename])
        args.append("--single-version-externally-managed")

        if root is not None:
            args.extend(["--root", root])

        # TODO: Confirm, then in its own change.
        args.extend(["--prefix", prefix])

        args.append("--compile" if pycompile else "--no-compile")

        # TODO: Confirm, then in its own change.
        args.extend(["--install-headers", headers])

    def install_editable_args(
        self,
        setup_py_path,
        global_options,
        install_options,
        scheme,
    ):
        prefix = scheme["prefix"]

        args = make_setuptools_shim_args(
            setup_py_path,
            global_options=global_options,
            no_user_config=self._isolated,
        )

        args.extend(["develop", "--no-deps"])
        args.extend(install_options)
        args.extend(["--prefix", prefix])
        return args

    def wheel_args(
        self,
        setup_py_path,
        global_options,
        build_options,
        destination_dir,
        python_tag,
    ):
        args = make_setuptools_shim_args(
            setup_py_path, global_options=global_options, unbuffered_output=True
        )
        args.extend(["bdist_wheel", "-d", destination_dir])
        if python_tag is not None:
            args.extend(["--python-tag", python_tag])
        return args


def legacy_editable_install(
    setup_py_path,
    isolated,
    name,
    install_options,
    global_options,
    prefix,
    build_env,
    unpacked_source_directory,
):
    pass


def get_install_args(
    setup_py_path,
    global_options,
    scheme,
    root,
    pycompile,
):
    pass


def legacy_install(
    setup_py_path,
    isolated,
    name,
    install_options,
    global_options,
    root,
    home,
    prefix,
    use_user_site,
    pycompile,
):
    pass


def unpacked_wheel_install(
    source_dir,
    name,
    root,
    prefix,
    home,
    warn_script_location,
    use_user_site,
    pycompile,
):
    pass
