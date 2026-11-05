# Local JIDT dependency

- **source/**: pinned official JIDT checkout, moved from vendor/jidt-official/. Source algorithms are unmodified.
- **build/**: existing infodynamics.jar and build manifest/logs, moved from lib/jidt-official/.

The exact build commit/hash is preserved in build/build_manifest.json. Historical manifest commands retain their original paths. src/primary_information.py verifies the actual relocated jar/source and returns the current jar path to other application runners. Build only if needed with `.venv/bin/python src/build_jidt_official.py` from the project root. Disposable compiled-class caches were removed; the build script recreates them when needed. The source checkout and generated Java class files remain ignored by the parent repository.
