import sys
import os
import zlib
import hashlib


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command =='cat-file':
        if sys.argv[2] == '-p':
            blob_sha = sys.argv[3]
            with open(f".git/objects/{blob_sha[:2]}/{blob_sha[2:]}", "rb") as f:
                raw = zlib.decompress(f.read())
                header, content = raw.split(b"\0", maxsplit=1)
                print(content.decode("utf-8"), end="")
            
        elif command == "hash-object":
            if sys.argv[2] == "-w":
            ## write object to .git/objects
                file_name = sys.argv[3]
                content = open(file_name, "rb").read()
                header = f"blob {len(content)}\0".encode()
                sha = hashlib.sha1(header + content).hexdigest()
                os.makedirs(f".git/objects/{sha[:2]}", exist_ok=True)
                with open(f".git/objects/{sha[:2]}/{sha[2:]}", "wb") as f:
                    f.write(zlib.compress(header + content))
                print(sha)
            else:
                ## prints a 40-character SHA hash to stdout
                file_name = sys.argv[3]
                content = open(file_name, "rb").read()
                header = f"blob {len(content)}\0".encode()
                sha = hashlib.sha1(header + content).hexdigest()
                print(sha)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
