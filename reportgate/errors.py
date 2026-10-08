"""Exceptions raised by reportgate."""


class ReportgateError(Exception):
    """Base class for errors that stop a triage run."""


class ReportDirError(ReportgateError, ValueError):
    """The reports directory is missing, is not a directory, or holds no reports.

    The command line turns this into exit code 2.
    """


class CheckoutError(ReportgateError, ValueError):
    """The checkout given with ``repo=`` / ``--repo`` is not a directory.

    The command line turns this into exit code 2.
    """
