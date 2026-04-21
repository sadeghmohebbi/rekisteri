import json
import requests
import os

def fetch_provider_data(namespace, provider_type, specific_version=None, specific_os=None, specific_arch=None):
    """Fetch provider versions and platform details from public registry."""
    base_url = "https://registry.terraform.io/v1/providers"
    versions_url = f"{base_url}/{namespace}/{provider_type}/versions"
    
    # Get the list of versions and their platforms
    resp = requests.get(versions_url)
    resp.raise_for_status()
    versions_data = resp.json()
    
    versions = []
    for version_info in versions_data.get("versions", []):
        version = version_info["version"]

        if (specific_version and version != specific_version):
            continue

        platforms = []
        # For each platform listed in the version, fetch download details
        for platform in version_info.get("platforms", []):
            if (specific_os and platform["os"] != specific_os) or (specific_arch and platform["arch"] != specific_arch):
                continue
            os_name = platform["os"]
            arch = platform["arch"]
            download_url = f"{base_url}/{namespace}/{provider_type}/{version}/download/{os_name}/{arch}"
            download_resp = requests.get(download_url)
            download_resp.raise_for_status()
            download_data = download_resp.json()
            
            platforms.append({
                "os": os_name,
                "arch": arch,
                "filename": download_data["filename"],
                "download_url": download_data["download_url"],
                "shasums_url": download_data["shasums_url"],
                "shasums_signature_url": download_data["shasums_signature_url"],
                "shasum": download_data["shasum"],
                "signing_keys": download_data["signing_keys"]
            })
        
        versions.append({
            "version": version,
            "protocols": version_info.get("protocols", []),
            "platforms": platforms
        })
    
    return {"versions": versions}

def save_provider_file(namespace, provider_type, output_dir="providers", specific_version=None, specific_os=None, specific_arch=None):
    """Save the provider JSON file in rekisteri's expected directory structure."""
    os.makedirs(output_dir, exist_ok=True)
    provider_dir = os.path.join(output_dir, namespace)
    os.makedirs(provider_dir, exist_ok=True)
    
    filepath = os.path.join(provider_dir, f"{provider_type}.json")
    data = fetch_provider_data(
        namespace,
        provider_type,
        specific_version=specific_version,
        specific_os=specific_os,
        specific_arch=specific_arch
    )
    
    # Download zip files and modify download_urls
    os.makedirs("downloads", exist_ok=True)
    for version_data in data["versions"]:
        for platform in version_data["platforms"]:
            download_url = platform["download_url"]
            filename = platform["filename"]
            download_dir = os.path.join("downloads", namespace, provider_type, version_data["version"], platform["os"], platform["arch"])
            os.makedirs(download_dir, exist_ok=True)
            filepath_zip = os.path.join(download_dir, filename)
            print(f"Downloading {download_url} to {filepath_zip}")
            resp = requests.get(download_url)
            resp.raise_for_status()
            with open(filepath_zip, "wb") as f:
                f.write(resp.content)
            # Modify the download_url
            platform["download_url"] = f"http://localhost:5000/downloads/{namespace}/{provider_type}/{version_data['version']}/{platform['os']}/{platform['arch']}"
        
        # Download shasums files
        if version_data["platforms"]:
            shasums_url = version_data["platforms"][0]["shasums_url"]
            shasums_sig_url = version_data["platforms"][0]["shasums_signature_url"]
            download_dir = os.path.join("downloads", namespace, provider_type, version_data["version"])
            print(f"Downloading {shasums_url} to {os.path.join(download_dir, 'SHA256SUMS')}")
            resp = requests.get(shasums_url)
            resp.raise_for_status()
            with open(os.path.join(download_dir, "SHA256SUMS"), "wb") as f:
                f.write(resp.content)
            print(f"Downloading {shasums_sig_url} to {os.path.join(download_dir, 'SHA256SUMS.sig')}")
            resp = requests.get(shasums_sig_url)
            resp.raise_for_status()
            with open(os.path.join(download_dir, "SHA256SUMS.sig"), "wb") as f:
                f.write(resp.content)
            # Modify the shasums urls
            for platform in version_data["platforms"]:
                platform["shasums_url"] = f"http://localhost:5000/v1/providers/{namespace}/{provider_type}/{version_data['version']}/shasums"
                platform["shasums_signature_url"] = f"http://localhost:5000/v1/providers/{namespace}/{provider_type}/{version_data['version']}/shasums.sig"
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {filepath}")

if __name__ == "__main__":
    # Generate for both providers
    save_provider_file("hashicorp", "vsphere", specific_version="2.4.1", specific_os="linux", specific_arch="amd64")
    # save_provider_file("hashicorp", "local")