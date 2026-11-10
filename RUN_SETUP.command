#!/bin/bash
cd "$(dirname "$0")" || exit 1

echo "======================================================="
echo "      SheetLink-MCP 1-Click Installation Setup"
echo "      Author: Saikat (github.com/saikatcloudhere)"
echo "======================================================="
echo ""

setup_error() {
    echo "[ERROR] Setup did not complete. Check your internet connection and reopen this launcher to retry."
    read -r -p "Press Enter to exit..."
    exit 1
}

tools_dir="$PWD/.setup-tools"
export UV_PYTHON_INSTALL_DIR="$tools_dir/python"
uv="$tools_dir/uv"

if ! "$uv" --version >/dev/null 2>&1; then
    echo "[1/3] Downloading the setup tool..."
    case "$(uname -m)" in
        arm64)
            asset="uv-aarch64-apple-darwin"
            expected="81b811b57e4624df7ed3aac148e0359100d9962f3d9dce00aec533dc2e086731"
            ;;
        x86_64)
            asset="uv-x86_64-apple-darwin"
            expected="20c47e4c1f630b8abaff8c291fa9b9aa300fef92c4fbff95adf198b55287cda7"
            ;;
        *)
            echo "[ERROR] This installer requires a 64-bit Intel or Apple Silicon Mac."
            setup_error
            ;;
    esac
    mkdir -p "$tools_dir" || setup_error
    archive="$tools_dir/uv-download.tar.gz"
    curl --proto '=https' --tlsv1.2 -fsSL --retry 2 \
        "https://releases.astral.sh/github/uv/releases/download/0.13.7/$asset.tar.gz" \
        -o "$archive" || setup_error
    digest="$(shasum -a 256 "$archive")" || setup_error
    if [ "${digest%% *}" != "$expected" ]; then
        echo "[ERROR] Setup tool checksum did not match."
        setup_error
    fi
    tar -xzf "$archive" -C "$tools_dir" --strip-components 1 "$asset/uv" || setup_error
    rm -f -- "$archive"
fi

echo "[2/3] Preparing Python and SheetLink-MCP..."
if ! ".venv/bin/python" -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    "$uv" --no-config venv --managed-python --python 3.13 --clear .venv || setup_error
fi
"$uv" --no-config pip install --python ".venv/bin/python" -r requirements.txt || setup_error

echo "[3/3] Opening setup in your browser..."
".venv/bin/python" setup_wizard.py "$@" || setup_error
