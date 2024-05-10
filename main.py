from llama_index.llms.openai import OpenAI  # type: ignore
from llama_index.embeddings.openai import OpenAIEmbedding  # type: ignore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.readers.github import GithubRepositoryReader, GithubClient  # type: ignore
import logging
import streamlit as st
import re
import os

EMBED_MODEL = "text-embedding-3-small"
LLM = "gpt-4-turbo"
REPO_PATTERN = r"https://github\.com/([^/]+)/([^/]+)"

Settings.llm = OpenAI(model=LLM)
Settings.embed_model = OpenAIEmbedding(model=EMBED_MODEL)

if "index" not in st.session_state:
    st.session_state["index"] = None

st.set_page_config(
    page_title="Code Assistant",
    initial_sidebar_state="expanded",
    menu_items={"About": "Built by @seankim658 with Streamlit and LlamaIndex."},
)


def sidebar():

    with st.sidebar.expander("OpenAI API Key", expanded=True):
        st.text_input("Enter your API key", type="password", key="openai_api_key")
        st.markdown(
            "[Help](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)"
        )
        if st.session_state.openai_api_key:
            os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key

    with st.sidebar.expander("Github Personal Access Token", expanded=True):
        if "github_pat" not in st.session_state:
            st.session_state.github_pat = ""
        st.text_input(
            "Enter your personal access token", type="password", key="github_pat"
        )
        st.markdown(
            "[Help](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)"
        )


def layout():

    st.header("Chat with a Github Repository!")

    if not st.session_state.get("openai_api_key") or not st.session_state.get(
        "github_pat"
    ):

        if not st.session_state.get("openai_api_key"):
            st.warning("Please enter your OpenAI API Key", icon="🚨")

        if not st.session_state.get("github_pat"):
            st.warning("Please enter your Github Personal Access Token", icon="🚨")

    else:

        repo_config()

        index = st.session_state.get("index")
        if index:
            chat_engine = index.as_chat_engine(chat_mode="context")

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Ask a question about the repository.",
                }
            ]

        user_input = st.chat_input("Ask a question")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
        display_chat_history(st.session_state.messages)

        if st.session_state.messages[-1]["role"] != "assistant":
            try:
                generate_assistant_response(user_input, chat_engine)
            except Exception as e:
                st.error(str(e))


def generate_assistant_response(prompt: str, chat_engine: BaseChatEngine):
    
    with st.chat_message("assistant"):
        with st.spinner("On it..."):
            response = chat_engine.chat(prompt)
            message = {"role": "assistant", "content": response.response}
            st.write(message["content"])
            st.session_state.messages.append(message)

def display_chat_history(messages: list):

    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def repo_config() -> bool:

    github_client = GithubClient(st.session_state.get("github_pat"))

    url_input = st.text_input(
        "Enter the Github Repository URL to index.", key="github_repo_url"
    )
    branch = st.text_input(
        "Enter the repo branch to index (leave blank to default to `main`).",
        key="branch",
    )
    directories = st.text_input(
        "Enter directory paths to filter on separated by commas (or leave empty to not use).",
        key="directories",
    )
    directory_filter = st.radio(
        "Include or exclude these directories?",
        ["Include", "Exclude"],
        key="directory_filter",
    )
    file_extensions = st.text_input(
        "Enter file extensions to filter on separated by commas (or leave empty to not use).",
        key="file_extensions",
    )
    file_extension_filter = st.radio(
        "Include or exclude these file extensions?",
        ["Include", "Exclude"],
        key="file_extensions_filter",
    )

    if st.button("Load Repository"):

        if url_input:

            url = url_input.strip().lower()
            match = re.match(REPO_PATTERN, url)

            if match:

                directories = [dir.strip() for dir in directories.split(",") if dir.strip()]  # type: ignore
                file_extensions = [ext.strip() for ext in file_extensions.split(",") if ext.strip()]  # type: ignore
                directory_filter_type = GithubRepositoryReader.FilterType.INCLUDE if directory_filter.lower() == "include" else GithubRepositoryReader.FilterType.EXCLUDE  # type: ignore
                file_extension_filter_type = GithubRepositoryReader.FilterType.INCLUDE if file_extension_filter.lower() == "include" else GithubRepositoryReader.FilterType.EXCLUDE  # type: ignore
                branch = branch.lower().strip()
                branch_arg = branch if branch is not None and branch != "" else "main"

                owner, repo = match.groups()
                directory_arg = (
                    (directories, directory_filter_type)
                    if len(directories) > 0
                    else None
                )
                file_extension_arg = (
                    (file_extensions, file_extension_filter_type)
                    if len(file_extensions)
                    else None
                )

                git_loader = GithubRepositoryReader(
                    github_client=github_client,
                    owner=owner,
                    repo=repo,
                    filter_directories=directory_arg,
                    filter_file_extensions=file_extension_arg,
                )
                try:
                    github_documents = git_loader.load_data(branch=branch_arg)
                except Exception as _:
                    st.error(
                        "Error loading github reposistory, check your github token and repository information."
                    )
                    return False
                index = VectorStoreIndex.from_documents(github_documents)
                st.session_state["index"] = index

                return True
            else:
                st.error("Failed parsing repository URL, please try again.")
                return False


def main():
    sidebar()
    layout()


if __name__ == "__main__":
    main()
