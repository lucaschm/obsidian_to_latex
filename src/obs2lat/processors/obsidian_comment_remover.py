import re

from .content_processor import ContentProcessor


class ObsidianCommentRemover(ContentProcessor):

    COMMENT_PATTERN = re.compile(
        r"%%.*?%%",
        re.DOTALL,
    )

    def process(self, text: str) -> str:
        return self.COMMENT_PATTERN.sub("", text)