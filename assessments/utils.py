import re

from assessments.models import Assessment, Question


def generate_assessment_code():
    """
    Generate Assessment Code like:
    TMP0001
    TMP0002
    TMP0003
    """

    prefix = "TMP"

    codes = (
        Assessment.objects
        .filter(assessment_code__startswith=prefix)
        .values_list("assessment_code", flat=True)
    )

    max_number = 0

    for code in codes:

        match = re.search(r"(\d+)$", code)

        if match:
            max_number = max(
                max_number,
                int(match.group(1))
            )

    return f"{prefix}{max_number + 1:04d}"

def generate_question_code(subsection):
    """
    Generate Question Code
    Example:
        Logical Reasoning -> LR-0001
        Verbal Ability -> VA-0001
    """

    # Create prefix from subsection name
    words = subsection.name.strip().split()

    if len(words) == 1:
        prefix = words[0][:2].upper()
    else:
        prefix = "".join(word[0].upper() for word in words)

    # Get last question code for this prefix
    last_question = (
        Question.objects.filter(question_code__startswith=f"{prefix}-")
        .order_by("-question_code")
        .first()
    )

    if last_question:
        match = re.search(r"(\d+)$", last_question.question_code)
        last_number = int(match.group(1)) if match else 0
    else:
        last_number = 0

    new_number = last_number + 1

    return f"{prefix}-{new_number:04d}"