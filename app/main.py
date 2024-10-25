import sys
import os
import zlib
import hashlib


def compute_sha(file_name):
    content = open(file_name, "rb").read()
    header = f"blob {len(content)}\0".encode()
    sha = hashlib.sha1(header + content).hexdigest()
    return sha

def read_tree(tree_sha):
    with open(f".git/objects/{tree_sha[:2]}/{tree_sha[2:]}", "rb") as f:
        raw = zlib.decompress(f.read())
        header, content = raw.split(b"\0", maxsplit=1)
        return content

def print_tree_content(content, options=""):
    index = 0
    while index < len(content):
        mode_end = content.find(b' ', index)
        mode = content[index:mode_end].decode('utf-8')
        index = mode_end + 1

        sha_start = content.find(b'\0', index)
        name = content[index:sha_start].decode('utf-8', errors='ignore')
        sha = content[sha_start + 1:sha_start + 21].hex()
        index = sha_start + 21

        type_ = "blob"
        if mode == "40000":
            type_ = "tree"
        elif mode in ["100755", "100644", "120000"]:
            type_ = "blob"
        if options == "name-only":
            print(f"{name}")
        else:
            print(f"{mode} {type_} {sha} {name}")

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

    elif command == 'ls-tree':
        if sys.argv[2] == "--name-only":
            options = "name-only"
            tree_sha = sys.argv[3]
        else:
            options = "complete-view"
            tree_sha = sys.argv[2]
        content = read_tree(tree_sha)
        print_tree_content(content, options=options)
    
    elif command == 'write-tree':
        # get all files and folders in the current directory
        files = os.listdir()
        tree_content = b""
        print(files)
        
        
        pass

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
