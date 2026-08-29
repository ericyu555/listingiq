"""
ListingIQ - Streamlit UI.

Run from the project root:
    ~/venvs/listingiq/bin/streamlit run src/app.py
"""

import streamlit as st
from optimize import optimize

st.set_page_config(page_title="ListingIQ", page_icon="🛍️", layout="centered")

st.title("🛍️ ListingIQ")
st.caption("Paste a product listing. Get an optimized version — and an honest "
           "read on what was weak about the original.")


# ---------------------------------------------------------------------------
# TODO 1 - the two input boxes.
#
# st.text_input(label)   one line
# st.text_area(label)    multiple lines - takes height=200 as a second argument
#
# Each one RETURNS what the user typed, so you assign it to a variable:
#     something = st.text_input("Some label")
#
# Make a one-line input for the title, and a tall box for the description.
# ---------------------------------------------------------------------------

title = st.text_input("Product title")          # <- one-line input, label it "Product title"
description = st.text_area("Product description", height=200)     # <- text area, label it "Product description", height=200


# ---------------------------------------------------------------------------
# TODO 2 - call optimize() when the button is clicked.
#
# st.button("label", type="primary") returns True on the run where it was
# clicked, False otherwise. So the pattern is:
#
#     if st.button("Optimize listing", type="primary"):
#         ...do the work...
#
# Inside that block, wrap the call in a spinner so the user knows it's alive:
#
#     with st.spinner("Analyzing your listing..."):
#         result = optimize(title, description)
#
# Leave the validation and error handling below exactly as written - just
# fill in the two marked lines.
# ---------------------------------------------------------------------------

clicked = st.button("Optimize listing", type="primary")   # <- the st.button(...) call

if clicked:
    if not title.strip() or not description.strip():
        st.warning("Fill in both the title and the description.")
    else:
        try:
            with st.spinner("Analyzing your listing..."):
                result = optimize(title, description)

        except Exception as e:
            st.error(f"Something went wrong: {e}")

        else:
            # ---- everything below here is done, no edits needed ----
            st.divider()

            st.subheader("Optimized title")
            st.code(result.title, language=None, wrap_lines=True)

            st.subheader("Optimized description")
            st.code(result.description, language=None, wrap_lines=True)

            st.subheader("Bullets")
            for b in result.bullets:
                st.markdown(f"- {b}")

            st.subheader("Meta description")
            st.code(result.meta_description, language=None, wrap_lines=True)
            st.caption(f"{len(result.meta_description)} characters "
                       "(aim for roughly 155)")

            st.divider()
            st.subheader("What was weak about the original")
            for i, issue in enumerate(result.issues, 1):
                with st.expander(f"{i}. {issue.problem}"):
                    st.write(issue.why_it_matters)
