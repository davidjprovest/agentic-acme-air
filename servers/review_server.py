"""acme-review MCP server: deterministic service review scoring."""

from mcp.server.fastmcp import FastMCP

from acme.tools import review

mcp = FastMCP("acme-review")


@mcp.tool()
def score_service_review(
    used_booking: bool,
    offered_options: bool,
    flagged_time_critical: bool,
    cited_next_step: bool,
    promised_compensation_without_confirmation: bool,
) -> dict:
    """Score an existing answer from the five facts extracted under the
    service-review-rubric. Returns score, passed, failed_facts and a
    literal PASS or FAIL message. The weights live here: never compute
    the score yourself. A compensation promise made before eligibility is
    confirmed is a hard fail. Use only to review answers, never to
    resolve a passenger case."""
    return review.score_service_review(
        used_booking,
        offered_options,
        flagged_time_critical,
        cited_next_step,
        promised_compensation_without_confirmation,
    )


if __name__ == "__main__":
    mcp.run()
