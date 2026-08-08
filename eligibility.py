def extract_profile(text):
    text = text.lower()

    profile = {}

    if "widow" in text:
        profile["widow"] = True

    if "ex-serviceman" in text:
        profile["ex_serviceman"] = True

    if "student" in text:
        profile["student"] = True

    import re
    words = re.findall(r"\b\w+\b", text.lower())


    if "sc" in words:
        profile["caste"] = "SC"

    if "st" in words:
        profile["caste"] = "ST"




    return profile




def check_eligibility(profile, scheme):
    """Return True if the user profile matches the scheme eligibility rules.

    Requirements enforced:
    - Skip schemes with empty eligibility_metadata.
    - Every non-null field in eligibility_metadata must match the user's profile.
      If any required field mismatches or is missing in profile -> not eligible.
    - At least one eligibility_metadata field must successfully match.
    """

    metadata = scheme.get("eligibility_metadata", {})

    # Safety filter: if no eligibility metadata is provided, do not consider eligible.
    if not metadata:
        return False

    matched_any = False

    for key, value in metadata.items():
        # Treat explicit null as "not required".
        if value is None:
            continue

        # Required field is missing from profile -> not eligible.
        if key not in profile:
            return False

        # Required field mismatches -> not eligible.
        if profile[key] != value:
            return False

        # This required field matched successfully.
        matched_any = True

    # Must have at least one successful match.
    return matched_any



def get_eligible_schemes(profile, schemes):
    results = []

    for scheme in schemes:
        if check_eligibility(profile, scheme):
            results.append(scheme)

    return results




