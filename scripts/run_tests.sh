#!/bin/bash

# This script runs the tests for the bioscopeai-core project.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

source /var/www/bioscopeai-core/app/bioscopeai_core_env/bin/activate
pytest -p pytest_github_actions_annotate_failures --junitxml=results/pytest-results.xml --html=results/pytest-report.html --self-contained-html
