import streamlit as st
from components.layout import init, require_results
from exports.proposal import build_proposal, build_onepager

init("Funding Case", "How do we communicate this to a funder?", step=5)
r = require_results()
st.markdown(build_proposal(r))
a, b = st.columns(2)
a.download_button("Generate Funding Proposal", build_proposal(r), "sunsafe_proposal.md")
b.download_button("Generate Community One-Pager", build_onepager(r), "sunsafe_community_onepager.md")
