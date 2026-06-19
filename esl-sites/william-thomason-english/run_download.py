"""run_download.py - Wrapper to set env vars and run download with Pexels primary"""
import os, sys

os.environ["PEXELS_API_KEY"] = "9Q7efomkBnxybCH80DrHL7zVrYLNEIAmmIKsOGgg436PRQnba1xVU8Gj"
os.environ["PIXABAY_API_KEY"] = "17679031-5d7d8fa32547b732dfd53b91a"

sys.argv[0] = "download_images.py"
exec(open("download_images.py").read())
