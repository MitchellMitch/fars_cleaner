"""
Load sample data.
"""
import os
import hashlib
import zipfile
from pathlib import Path
from tqdm import tqdm
import shutil
import subprocess

class FARSFetcher:
    def __init__(self,
                 cache_path=None,
                 registry=None,
                 project_dir=None,
                 check_hash=True,
                 show_progress=True,
                 ):
        """Class to download FARS data from the NHTSA FTP repository.

        Note that on first run, this will take a long time to fully download the data, as the repository is large.
        Expect first run to take 5-10+ minutes, depending on your setup.

        Parameters
        ----------
        cache_path: `os.path` or path-like, or str, optional
            The path to save the downloaded FARS files to.
            Default is `~/.cache/fars`, a cache folder in the user's home directory.
            If `str`, and `project_dir` is not `None`, files will be downloaded to `project_dir/cache_path`
        registry:
            Path to registry file. Defaults to path for packaged `registry.txt` file. Override at your own risk.
        project_dir:
            Top level directory for your current project. If a path is provided, and `cache_path` is left as default,
            files will be downloaded to `project_dir/data/fars`. If `cache_path` is not the default, files will be
            downloaded to `project_dir/cache_path`.
        check_hash: bool
            Flag to enforce download behavior. Defaults to True. When False, force download of FARS resources
            regardless of hash mismatch against the local registry version. Useful for when the FARS
            database is updated before the registry can be modified. Should normally be left to default (False).
        show_progress: bool
            Show progress bars during download. Default True.
        """
        if project_dir:
            self.project_dir = project_dir
            if cache_path:
                self.cache_path = Path(project_dir) / cache_path
            else:
                self.cache_path = Path(project_dir) / "data" / "fars"
            self.project_dir.mkdir(parents=True, exist_ok=True)
            self.cache_path.mkdir(parents=True, exist_ok=True)
        else:
            self.project_dir = None
            if cache_path:
                self.cache_path = Path(cache_path)
                self.cache_path.mkdir(parents=True, exist_ok=True)
            else:
                # Default cache path in user's home directory
                self.cache_path = Path.home() / ".cache" / "fars"
                self.cache_path.mkdir(parents=True, exist_ok=True)

        if registry:
            self.registry = Path(registry)
        else:
            self.registry = os.path.join(os.path.dirname(__file__), "registry.txt")

        self.check_hash = check_hash
        self.show_progress = show_progress
        self.registry_dict = self._load_registry()

    def _load_registry(self):
        """Load the registry file into a dictionary mapping filename to (hash, url)."""
        registry_dict = {}
        with open(self.registry, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        filename, file_hash, url = parts[0], parts[1], parts[2]
                        registry_dict[filename] = (file_hash, url)
        return registry_dict
    
    def _verify_hash(self, file_path, expected_hash):
        """Verify the SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() == expected_hash
    
    def _download_file(self, url, target_path):
        """Download a file with progress bar using curl (HTTP/1.1)."""
        print(f"Sending request to {url}")
        try:
            # Construct the curl command
            curl_command = [
                'curl',
                '--http1.1',
                '-L',  # Follow redirects
                '-o', str(target_path),  # Output to target_path
                url
            ]

            if self.show_progress:
                curl_command.extend(['-#']) # Show progress bar
            else:
                curl_command.extend(['-sS']) # Silent mode with error reporting


            print(f"Executing command: {' '.join(curl_command)}")

            # Execute the command.
            # If check=True, CalledProcessError is raised for non-zero exit codes.
            # By not using capture_output=True (or stdout/stderr=PIPE),
            # curl's stderr (where progress or errors go) will be printed to the terminal.
            subprocess.run(curl_command, check=True, text=True)

            print(f"Download completed: {target_path}")

        except subprocess.CalledProcessError as e:
            # e.stderr will contain the error output from curl.
            error_message = e.stderr if e.stderr else "Curl command failed with no specific error message on stderr."
            if e.stdout: # curl -o writes to file, so stdout is usually not where errors are for this command.
                error_message += f"\nstdout: {e.stdout}"
            print(f"Error during download (subprocess.CalledProcessError): {error_message}")
            raise
        except Exception as e:
            print(f"Error during download: {str(e)}")
            raise
    
    def _extract_zip(self, zip_path, extract_dir):
        """Extract a zip file."""
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Set up progress bar for extraction if show_progress is True
            if self.show_progress:
                members = zip_ref.namelist()
                for member in tqdm(members, desc=f"Extracting {os.path.basename(zip_path)}"):
                    zip_ref.extract(member, extract_path)
            else:
                zip_ref.extractall(extract_path)
        
        # Return list of extracted files
        extracted_files = []
        for root, _, files in os.walk(extract_path):
            for file in files:
                extracted_files.append(os.path.join(root, file))
        
        return extracted_files
    
    def _get_file(self, filename):
        """Download and verify a single file."""
        if filename not in self.registry_dict:
            raise FileNotFoundError(f"{filename}: File not found in registry.")
        
        file_hash, url = self.registry_dict[filename]
        file_path = self.cache_path / filename
        
        print(f"Preparing to download {filename} from {url}")
        print(f"Target path: {file_path}")
        
        # Check if file exists and has correct hash
        download_needed = True
        if file_path.exists() and self.check_hash:
            print(f"File {filename} exists, checking hash...")
            if self._verify_hash(file_path, file_hash):
                print(f"Hash verification passed, skipping download")
                download_needed = False
            else:
                print(f"Hash verification failed, will download again")
        
        # Download if needed
        if download_needed:
            print(f"Starting download of {filename}...")
            self._download_file(url, file_path)
            
            # Verify hash after download
            if self.check_hash and not self._verify_hash(file_path, file_hash):
                raise ValueError(f"Hash verification failed for {filename}")
        
        return file_path

    def fetch_all(self):
        """
        Download the entire FARS dataset, to cache folder.
        """
        unzipped = {}
        
        for filename in self.registry_dict:
            try:
                if "dict" in filename:
                    self._get_file(filename)
                else:
                    file_path = self._get_file(filename)
                    extract_dir = self.cache_path / f"{filename[:-4]}.unzip"
                    unzipped[filename] = self._extract_zip(file_path, extract_dir)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                
        return unzipped

    def fetch_subset(self, start_yr, end_yr):
        """
        Download a subset of the FARS dataset.
        """
        unzipped = {}
        for yr in range(start_yr, end_yr + 1):
            unzipped[yr] = self.fetch_single(yr)
        return unzipped

    def fetch_single(self, year):
        """
        Load the FARS data for a given year.
        """
        filename = f'{year}.zip'
        try:
            file_path = self._get_file(filename)
            extract_dir = self.cache_path / f"{filename[:-4]}.unzip"
            extracted_files = self._extract_zip(file_path, extract_dir)
            return {year: extracted_files}
        except FileNotFoundError:
            raise FileNotFoundError(f"{filename}: File could not be found in FARS registry.")

    def fetch_mappers(self):
        """
        Loads the mappings for each variable from a pickled dictionary.

        Returns
        -------
        Path to the mapper file
        """
        return self._get_file("mapping.dict")

    def get_data_path(self):
        return self.cache_path
    
    def get_show_progress(self):
        return self.show_progress
