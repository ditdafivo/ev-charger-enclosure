#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_dir=$(cd -- "${script_dir}/.." && pwd)
repository_dir=$(git -C "${project_dir}" rev-parse --show-toplevel)
source_dir="${project_dir}/openscad-playground"
model_path=${1:-"${repository_dir}/pages/model.scad"}
output_dir=${2:-"${project_dir}/dist"}
build_id=${3:-local}
model_asset="${repository_dir}/assets/components/ev_charger_plug/ev_charger_plug.stl"

for command_name in git npm sed tar; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Required command is missing: ${command_name}" >&2
    exit 1
  fi
done

if [[ ! -f ${source_dir}/package.json ]]; then
  echo "OpenSCAD Playground submodule is missing. Run: git submodule update --init" >&2
  exit 1
fi
if [[ ! -f ${model_path} ]]; then
  echo "Prepared Playground model is missing: ${model_path}" >&2
  exit 1
fi
if [[ ! -f ${model_asset} ]]; then
  echo "Model asset is missing: ${model_asset}" >&2
  exit 1
fi

temporary_dir=$(mktemp -d)
cleanup() {
  rm -rf -- "${temporary_dir}"
}
trap cleanup EXIT

build_dir="${temporary_dir}/source"
mkdir -p "${build_dir}"
git -C "${source_dir}" archive --format=tar --output="${temporary_dir}/source.tar" HEAD
tar -C "${build_dir}" -xf "${temporary_dir}/source.tar"

mkdir -p "${build_dir}/public/default-project"
install -m 0644 "${model_path}" "${build_dir}/public/default-project/model.scad"
install -m 0644 "${model_asset}" "${build_dir}/public/default-project/ev_charger_plug.stl"
install -m 0644 "${source_dir}/LICENSE.md" "${build_dir}/public/LICENSE.md"
sed -i 's#../assets/components/ev_charger_plug/ev_charger_plug\.stl#ev_charger_plug.stl#' \
  "${build_dir}/public/default-project/model.scad"

git -C "${build_dir}" apply "${project_dir}/patches/retry-library-downloads.patch"
git -C "${build_dir}" apply "${project_dir}/patches/default-project.patch"
sed -i "s/__PLAYGROUND_BUILD_ID__/${build_id}/g" \
  "${build_dir}/src/state/initial-state.ts"
printf '%s\n' \
  '# Corresponding source' \
  '' \
  'This site was built from:' \
  '' \
  "- Enclosure source: https://github.com/ditdafivo/ev-charger-enclosure/tree/${build_id}" \
  "- OpenSCAD Playground revision: $(git -C "${source_dir}" rev-parse HEAD)" \
  '- Complete licenses and notices: [LICENSE.md](LICENSE.md)' \
  >"${build_dir}/public/SOURCE.md"

(
  cd "${build_dir}"
  npm install
  npm run build:all
)

rm -rf -- "${output_dir}"
mkdir -p "${output_dir}"
cp -a "${build_dir}/dist/." "${output_dir}/"
touch "${output_dir}/.nojekyll"

echo "Static Pages site written to ${output_dir}"
