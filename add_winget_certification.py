import shutil
from pathlib import Path
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

WINGET_REPO = Path(
    r"C:\Users\selvanagalam\winget-pkgs"
)

ZENWORKS_REPO = Path(
    r"C:\Users\selvanagalam\zenworks-winget-test-repo"
)

SOURCE_MANIFESTS = WINGET_REPO / "manifests"

DESTINATION = (
    ZENWORKS_REPO
    / "CERTIFICATION"
    / "manifests"
)

# ============================================================
# PACKAGES TO COLLECT
# ============================================================

PACKAGES = [
    "Git.Git",
    "Microsoft.Git",
    "Microsoft.VisualStudioCode",
    "Mozilla.Firefox",
    "7zip.7zip",
    "Notepad++.Notepad++",
    "Microsoft.PowerToys",
    "Microsoft.DotNet.SDK",
    "Microsoft.DotNet.Runtime",
    "Docker.DockerDesktop",
    "Postman.Postman",
    "LibreOffice.LibreOffice",
    "VLC.VLC",
    "Microsoft.PowerShell",
]

# Remove duplicates while preserving order
PACKAGES = list(dict.fromkeys(PACKAGES))


# ============================================================
# READ PACKAGE IDENTIFIER
# ============================================================

def read_package_identifier(yaml_file):
    """
    Read PackageIdentifier from a YAML file.

    We only need to inspect the beginning of the file.
    This avoids reading the entire YAML unnecessarily.
    """

    try:
        with open(
            yaml_file,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            for line in f:

                line = line.strip()

                if line.startswith("PackageIdentifier:"):

                    return line.split(
                        ":", 1
                    )[1].strip()

    except Exception:
        return None

    return None


# ============================================================
# BUILD INDEX
# ============================================================

def build_manifest_index():
    """
    Scan winget-pkgs ONCE.

    Creates:

        PackageIdentifier
              |
              +--> manifest directory
              +--> manifest directory
              +--> ...

    Example:

        Git.Git
          -> manifests/g/Git/Git/2.36.0
          -> manifests/g/Git/Git/2.40.1
          -> manifests/g/Git/Git/2.47.1.2

    The directory structure itself is NOT used to determine
    PackageIdentifier.
    """

    print()
    print("=" * 70)
    print("BUILDING WINGET MANIFEST INDEX")
    print("=" * 70)

    print()
    print("Source:")
    print(SOURCE_MANIFESTS)

    print()
    print("Scanning YAML files once...")

    index = defaultdict(set)

    yaml_count = 0
    identifier_count = 0

    # Recursive scan happens ONLY ONCE
    for yaml_file in SOURCE_MANIFESTS.rglob("*.yaml"):

        yaml_count += 1

        identifier = read_package_identifier(
            yaml_file
        )

        if not identifier:
            continue

        identifier_count += 1

        # Store the directory containing the YAML
        index[identifier].add(
            yaml_file.parent
        )

        # Progress every 10,000 files
        if yaml_count % 10000 == 0:

            print(
                f"  Scanned {yaml_count:,} YAML files..."
            )

    print()
    print("Index completed.")

    print(
        f"YAML files scanned : {yaml_count:,}"
    )

    print(
        f"Identifiers found  : {len(index):,}"
    )

    print(
        f"Identifier entries  : {identifier_count:,}"
    )

    return index


# ============================================================
# FIND COMPLETE MANIFEST SET
# ============================================================

def get_manifest_sets(
    package_id,
    index
):
    """
    Get all directories containing YAML manifests
    for the requested PackageIdentifier.
    """

    directories = index.get(
        package_id,
        set()
    )

    results = []

    for directory in sorted(directories):

        yaml_files = list(
            directory.glob("*.yaml")
        )

        if yaml_files:

            results.append(
                (
                    directory,
                    yaml_files
                )
            )

    return results


# ============================================================
# COPY DIRECTORY
# ============================================================

def copy_manifest_directory(
    source_directory
):
    """
    Copy the COMPLETE manifest directory.

    The original winget-pkgs path is preserved.

    Example:

        manifests/
            g/
              Git/
                Git/
                  2.36.0/
                    *.yaml

    becomes:

        CERTIFICATION/
            manifests/
                g/
                  Git/
                    Git/
                      2.36.0/
                        *.yaml
    """

    try:

        relative_path = (
            source_directory.relative_to(
                SOURCE_MANIFESTS
            )
        )

    except ValueError:

        print(
            f"ERROR: Cannot calculate relative path:"
            f" {source_directory}"
        )

        return 0

    destination = (
        DESTINATION
        / relative_path
    )

    destination.mkdir(
        parents=True,
        exist_ok=True
    )

    yaml_files = list(
        source_directory.glob("*.yaml")
    )

    copied = 0

    print()
    print(
        f"  Source:"
    )

    print(
        f"    {source_directory}"
    )

    print(
        f"  Destination:"
    )

    print(
        f"    {destination}"
    )

    for yaml_file in yaml_files:

        target = (
            destination
            / yaml_file.name
        )

        shutil.copy2(
            yaml_file,
            target
        )

        print(
            f"      {yaml_file.name}"
        )

        copied += 1

    return copied


# ============================================================
# PROCESS PACKAGE
# ============================================================

def process_package(
    package_id,
    index
):

    print()
    print("=" * 70)
    print(
        f"PACKAGE: {package_id}"
    )
    print("=" * 70)

    manifest_sets = get_manifest_sets(
        package_id,
        index
    )

    if not manifest_sets:

        print()
        print(
            f"NOT FOUND: {package_id}"
        )

        return 0, 0

    print()
    print(
        f"Found {len(manifest_sets)} "
        f"manifest directory(s)"
    )

    total_yaml = 0

    for directory, yaml_files in manifest_sets:

        copied = copy_manifest_directory(
            directory
        )

        total_yaml += copied

    return (
        len(manifest_sets),
        total_yaml
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(" ZENworks Winget Certification Dataset Builder")
    print("=" * 70)

    print()
    print(
        f"Winget repository:"
    )

    print(
        f"  {WINGET_REPO}"
    )

    print()
    print(
        f"Manifest source:"
    )

    print(
        f"  {SOURCE_MANIFESTS}"
    )

    print()
    print(
        f"Certification destination:"
    )

    print(
        f"  {DESTINATION}"
    )

    # --------------------------------------------------------
    # Validate paths
    # --------------------------------------------------------

    if not WINGET_REPO.exists():

        print()
        print("ERROR:")
        print(
            f"Winget repository does not exist:"
        )
        print(
            f"  {WINGET_REPO}"
        )

        return

    if not SOURCE_MANIFESTS.exists():

        print()
        print("ERROR:")
        print(
            f"Manifest directory does not exist:"
        )
        print(
            f"  {SOURCE_MANIFESTS}"
        )

        return

    DESTINATION.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Build index ONCE
    # --------------------------------------------------------

    index = build_manifest_index()

    # --------------------------------------------------------
    # Process packages
    # --------------------------------------------------------

    total_packages = 0
    total_manifest_dirs = 0
    total_yaml_files = 0

    print()
    print("=" * 70)
    print("PROCESSING CERTIFICATION PACKAGES")
    print("=" * 70)

    for package_id in PACKAGES:

        manifest_count, yaml_count = (
            process_package(
                package_id,
                index
            )
        )

        if manifest_count > 0:

            total_packages += 1

            total_manifest_dirs += (
                manifest_count
            )

            total_yaml_files += (
                yaml_count
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(" COMPLETED")
    print("=" * 70)

    print()
    print(
        f"Packages requested       : "
        f"{len(PACKAGES)}"
    )

    print(
        f"Packages found           : "
        f"{total_packages}"
    )

    print(
        f"Manifest directories     : "
        f"{total_manifest_dirs}"
    )

    print(
        f"YAML files copied        : "
        f"{total_yaml_files}"
    )

    print()
    print(
        "Certification dataset:"
    )

    print(
        f"  {DESTINATION}"
    )

    print()
    print(
        "Next:"
    )

    print(
        "  git status"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()