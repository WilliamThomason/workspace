"""run_unsplash.py - Wrapper for Unsplash-only pass"""
import os, sys

os.environ["UNSPLASH_ACCESS_KEY"] = "GdmozKQKR1AYvpGeRq6xioPni2JQPKhbJi4BCwuDu6o"
os.environ["PIXABAY_API_KEY"] = "17679031-5d7d8fa32547b732dfd53b91a"

sys.argv = ["download_images.py", "--unsplash"]
exec(open("download_images.py").read())
