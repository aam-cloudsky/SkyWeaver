class MissingDependencyError(RuntimeError):
    def __init__(
        self,
        *,
        flow_name: str,
        node_name: str,
        missing_dependencies: list[str],
    ) -> None:
        missing = "\n".join(f"    {dependency}" for dependency in missing_dependencies)

        super().__init__(
            "MissingDependencyError\n\n"
            f"QueryFlow '{flow_name}'\n"
            f"cannot execute output node '{node_name}' because:\n"
            f"{missing}\n"
            "is not available."
        )
