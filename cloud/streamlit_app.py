"""Community Cloud entrypoint: one cached ResearchService, no API server required."""
import os
from pathlib import Path
import sys

# Community Cloud starts from repository root; local invocation may differ.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import streamlit as st
from app.client import APIClientError
from app.cloud_runtime import CloudSettings, DirectResearchClient, build_runtime
from app.streamlit_app import main as render_application


@st.cache_resource(max_entries=1, on_release=lambda runtime: runtime.close(),
                   show_spinner='Preparing the verified corpus, index and BGE model…')
def get_runtime():
    return build_runtime(CloudSettings.from_env())


def main():
    try:
        settings = CloudSettings.from_env()
    except APIClientError as error:
        st.title('ResearchLens')
        st.error(str(error))
        st.stop()
    st.caption('University demonstration: access is private. Question allowance and feedback use temporary local storage and may reset on cloud redeployment.')
    def client_factory():
        return DirectResearchClient(get_runtime(),
            authorized=lambda: bool(st.session_state.get('demo_authorized', False)),
            expires_at=settings.expires_at)
    render_application(client_factory, require_demo_password=True)


if __name__ == '__main__':
    main()
