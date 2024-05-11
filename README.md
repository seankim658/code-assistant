# Code Assistant

A simple RAG chat engine that allows you to chat with a Github repository. This tool was built to assist with learning someone else's codebase. 

## Usage

On startup you'll have to paste in your OpenAI API key as well as a Github personal access token. Then you can paste in your desired Github repository URL. The rest of the configuration options are optional:

- `Branch`: The desired branch in the repo to chat with (if left blank it will default to `main`).
- `Directory filter`: Enter the specific directory paths to either exclusively include or exclude.
- `Directory filter type`: `Include` will only consider the entered directory path(s) and `Exclude` will consider everything else except for the entered directory path(s).
- `File extension filter`: Enter the specifc file extensions to either exclusively include or exclude.
- `File extension filter type`: `Include` will only consider the entered file extension(s) and `Exclude` will consider everything else except for the entered file extension(s). 

Once your configuration options are set, click `Load Repository`.
