import sys
import os
import zlib
import hashlib
from pathlib import Path

from typing import Tuple, List, cast
import urllib.request
import struct


def init_repo(parent: Path):
    (parent / ".git").mkdir(parents=True)
    (parent / ".git" / "objects").mkdir(parents=True)
    (parent / ".git" / "refs").mkdir(parents=True)
    (parent / ".git" / "refs" / "heads").mkdir(parents=True)
    (parent / ".git" / "HEAD").write_text("ref: refs/heads/main\n")


def read_object(parent: Path, sha: str) -> Tuple[str, bytes]:
    pre = sha[:2]
    post = sha[2:]
    p = parent / ".git" / "objects" / pre / post
    bs = p.read_bytes()
    head, content = zlib.decompress(bs).split(b"\0", maxsplit=1)
    ty, _ = head.split(b" ")
    return ty.decode(), content

def write_object(parent: Path, ty: str, content: bytes) -> str:
    content = ty.encode() + b" " + f"{len(content)}".encode() + b"\0" + content
    hash = hashlib.sha1(content, usedforsecurity=False).hexdigest()
    compressed_content = zlib.compress(content, level=zlib.Z_BEST_SPEED)
    pre = hash[:2]
    post = hash[2:]
    p = parent / ".git" / "objects" / pre / post
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(compressed_content)
    return hash


def create_blob_entry(path, write=True):
    with open(path, "rb") as f:
        data = f.read()
    header = f"blob {len(data)}\0".encode("utf-8")
    store = header + data
    sha = hashlib.sha1(store).hexdigest()
    if write:
        os.makedirs(f".git/objects/{sha[:2]}", exist_ok=True)
        with open(f".git/objects/{sha[:2]}/{sha[2:]}", "wb") as f:
            f.write(zlib.compress(store))
    return sha
def write_tree(path: str):
    if os.path.isfile(path):
        return create_blob_entry(path)
    contents = sorted(
        os.listdir(path),
        key=lambda x: x if os.path.isfile(os.path.join(path, x)) else f"{x}/",
    )
    s = b""
    for item in contents:
        if item == ".git":
            continue
        full = os.path.join(path, item)
        if os.path.isfile(full):
            s += f"100644 {item}\0".encode()
        else:
            s += f"40000 {item}\0".encode()
        sha1 = int.to_bytes(int(write_tree(full), base=16), length=20, byteorder="big")
        s += sha1
    s = f"tree {len(s)}\0".encode() + s
    sha1 = hashlib.sha1(s).hexdigest()
    os.makedirs(f".git/objects/{sha1[:2]}", exist_ok=True)
    with open(f".git/objects/{sha1[:2]}/{sha1[2:]}", "wb") as f:
        f.write(zlib.compress(s))
    return sha1



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
    
    elif command == "write-tree":
        print(write_tree("./"))

    elif command == "commit-tree":
        # print("Calling commit tree")
        tree_sha = sys.argv[2]
        if sys.argv[3] == "-p":
            commit_sha = sys.argv[4]
            message = sys.argv[6]
        else:
            message = sys.argv[4]
        

        contents = b"".join(
            [
                b"tree %b\n" % tree_sha.encode(),
                b"parent %b\n" % commit_sha.encode(),
                b"author ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n",
                b"committer ggzor <30713864+ggzor@users.noreply.github.com> 1714599041 -0600\n\n",
                message.encode(),
                b"\n",
            ]
        )
        hash = write_object(Path("."), "commit", contents)
        print(hash)

    #####################################################################
    elif command == 'clone':
        url = sys.argv[2]
        dir = sys.argv[3]

        parent = Path(dir)
        init_repo(parent)
        # fetch refs
        req = urllib.request.Request(f"{url}/info/refs?service=git-upload-pack")
        with urllib.request.urlopen(req) as f:
            refs = {
                bs[1].decode(): bs[0].decode()
                for bs0 in cast(bytes, f.read()).split(b"\n")
                if (bs1 := bs0[4:])
                and not bs1.startswith(b"#")
                and (bs2 := bs1.split(b"\0")[0])
                and (bs := (bs2[4:] if bs2.endswith(b"HEAD") else bs2).split(b" "))
            }
        # render refs
        for name, sha in refs.items():
            Path(parent / ".git" / name).write_text(sha + "\n")
        # fetch pack
        body = (
            b"0011command=fetch0001000fno-progress"
            + b"".join(b"0032want " + ref.encode() + b"\n" for ref in refs.values())
            + b"0009done\n0000"
        )
        req = urllib.request.Request(
            f"{url}/git-upload-pack",
            data=body,
            headers={"Git-Protocol": "version=2"},
        )
        with urllib.request.urlopen(req) as f:
            pack_bytes = cast(bytes, f.read())
        pack_lines = []
        while pack_bytes:
            line_len = int(pack_bytes[:4], 16)
            if line_len == 0:
                break
            pack_lines.append(pack_bytes[4:line_len])
            pack_bytes = pack_bytes[line_len:]
        pack_file = b"".join(l[1:] for l in pack_lines[1:])
        def next_size_type(bs: bytes) -> Tuple[str, int, bytes]:
            ty = (bs[0] & 0b_0111_0000) >> 4
            match ty:
                case 1:
                    ty = "commit"
                case 2:
                    ty = "tree"
                case 3:
                    ty = "blob"
                case 4:
                    ty = "tag"
                case 6:
                    ty = "ofs_delta"
                case 7:
                    ty = "ref_delta"
                case _:
                    ty = "unknown"
            size = bs[0] & 0b_0000_1111
            i = 1
            off = 4
            while bs[i - 1] & 0b_1000_0000:
                size += (bs[i] & 0b_0111_1111) << off
                off += 7
                i += 1
            return ty, size, bs[i:]
        def next_size(bs: bytes) -> Tuple[int, bytes]:
            size = bs[0] & 0b_0111_1111
            i = 1
            off = 7
            while bs[i - 1] & 0b_1000_0000:
                size += (bs[i] & 0b_0111_1111) << off
                off += 7
                i += 1
            return size, bs[i:]
        # get objs
        pack_file = pack_file[8:]  # strip header and version
        n_objs, *_ = struct.unpack("!I", pack_file[:4])
        pack_file = pack_file[4:]
        for _ in range(n_objs):
            ty, _, pack_file = next_size_type(pack_file)
            match ty:
                case "commit" | "tree" | "blob" | "tag":
                    dec = zlib.decompressobj()
                    content = dec.decompress(pack_file)
                    pack_file = dec.unused_data
                    write_object(parent, ty, content)
                case "ref_delta":
                    obj = pack_file[:20].hex()
                    pack_file = pack_file[20:]
                    dec = zlib.decompressobj()
                    content = dec.decompress(pack_file)
                    pack_file = dec.unused_data
                    target_content = b""
                    base_ty, base_content = read_object(parent, obj)
                    # base and output sizes
                    _, content = next_size(content)
                    _, content = next_size(content)
                    while content:
                        is_copy = content[0] & 0b_1000_0000
                        if is_copy:
                            data_ptr = 1
                            offset = 0
                            size = 0
                            for i in range(0, 4):
                                if content[0] & (1 << i):
                                    offset |= content[data_ptr] << (i * 8)
                                    data_ptr += 1
                            for i in range(0, 3):
                                if content[0] & (1 << (4 + i)):
                                    size |= content[data_ptr] << (i * 8)
                                    data_ptr += 1
                            # do something with offset and size
                            content = content[data_ptr:]
                            target_content += base_content[offset : offset + size]
                        else:
                            size = content[0]
                            append = content[1 : size + 1]
                            content = content[size + 1 :]
                            # do something with append
                            target_content += append
                    write_object(parent, base_ty, target_content)
                case _:
                    raise RuntimeError("Not implemented")
        # render tree
        def render_tree(parent: Path, dir: Path, sha: str):
            dir.mkdir(parents=True, exist_ok=True)
            _, tree = read_object(parent, sha)
            while tree:
                mode, tree = tree.split(b" ", 1)
                name, tree = tree.split(b"\0", 1)
                sha = tree[:20].hex()
                tree = tree[20:]
                match mode:
                    case b"40000":
                        render_tree(parent, dir / name.decode(), sha)
                    case b"100644":
                        _, content = read_object(parent, sha)
                        Path(dir / name.decode()).write_bytes(content)
                    case _:
                        raise RuntimeError("Not implemented")
        _, commit = read_object(parent, refs["HEAD"])
        tree_sha = commit[5 : 40 + 5].decode()
        render_tree(parent, parent, tree_sha)




    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
