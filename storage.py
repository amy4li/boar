#!/usr/bin/python
from __future__ import with_statement

import md5
import os
import tempfile
import re
import simplejson as json

import repository
import shutil

def md5sum(data):
    m = md5.new()
    m.update(data)
    return m.hexdigest()

class RepoWriter:
    def __init__(self, repo):
        self.repo = repo
        self.session_path = None
        self.metadatas = []

    def new_session(self):
        assert self.session_path == None
        assert os.path.exists(self.repo.repopath)
        self.session_path = tempfile.mkdtemp( \
            prefix = "tmp_", 
            dir = os.path.join(self.repo.repopath, repository.TMP_DIR)) 

    def add(self, data, metadata = {}, original_sum = None):
        assert self.session_path != None
        sum = md5sum(data)
        if original_sum:
            assert sum == md5sum, "Calculated checksum did not match client provided checksum"
        metadata["md5sum"] = sum
        fname = os.path.join(self.session_path, sum)
        existing_blob_path = self.repo.get_blob_path(sum)
        existing_blob = os.path.exists(existing_blob_path)
        if not existing_blob and not os.path.exists(fname):
            with open(fname, "w") as f:
                f.write(data)
        self.metadatas.append(metadata)
        return sum

    def close_session(self, sessioninfo = {}):
        assert self.session_path != None

        bloblist_filename = os.path.join(self.session_path, "bloblist.json")
        assert not os.path.exists(bloblist_filename)
        with open(bloblist_filename, "w") as f:
            json.dump(self.metadatas, f, indent = 4)

        session_filename = os.path.join(self.session_path, "session.json")
        assert not os.path.exists(session_filename)
        with open(session_filename, "w") as f:
            json.dump(sessioninfo, f, indent = 4)

        queue_dir = self.repo.get_queue_path("queued_session")
        assert not os.path.exists(queue_dir)

        print "Committing to", queue_dir, "from", self.session_path, "..."
        shutil.move(self.session_path, queue_dir)
        print "Done committing."
        print "Consolidating changes..."
        id = self.repo.process_queue()
        print "Consolidating changes complete"
        return id

checked_blobs = {}

class SessionReader:
    def __init__(self, repo, session_id):
        self.path = repo.get_session_path(session_id)
        self.session_id = session_id
        self.repo = repo
        assert os.path.exists(self.path)
        self.session_info = json
        self.session_id = session_id

        path = os.path.join(self.path, "bloblist.json")
        with open(path, "r") as f:
            self.bloblist = json.load(f)

        path = os.path.join(self.path, "session.json")
        with open(path, "r") as f:
            self.session_info = json.load(f)

    def verify(self):
        for blobinfo in self.bloblist:
            sum = blobinfo['md5sum']
            if checked_blobs.has_key(sum):
                is_ok = checked_blobs[sum]
            else:
                is_ok = self.repo.verify_blob(blobinfo['md5sum'])
                checked_blobs[sum] = is_ok
            print blobinfo['filename'], is_ok

    
if __name__ == "__main__":
    main()

