[app]

# (str) Title of your application
title = AQL判定工具

# (str) Package name
package.name = aqlinspector

# (str) Package domain (needed for android/ios packaging)
package.domain = com.aql.inspector

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (relative to source.dir)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (relative to source.dir)
#source.exclude_exts = spec

# (list) List of directory to exclude (relative to source.dir)
#source.exclude_dirs = tests, bin

# (list) List of additional directories to search for Python modules
#search_path =

# (str) Presplash background color (in CSS format, e.g. "#ffffff")
presplash.color = #10101c

# (str) Icon file for the application
icon = icon.png

# (str) Application versioning
version = 1.0.0

# (str) Application build number (integer)
#version.build = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API level (default: 34)
android.api = 34

# (int) Minimum API level (default: 21)
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 24

# (str) Android NDK version to use
android.ndk = 27b

# (bool) Accept Android SDK license automatically
android.accept_sdk_license = True

# (str) Path to the Android SDK directory
#android.sdk_path =

# (str) Path to the Android NDK directory
#android.ndk_path =

# (str) Path to Java (ant/gradle)
#android.gradle_source_dir =

# (bool) If True, the app will always rotate with the device
android.allow_rotation = False

# (bool) If True, the app will be fullscreen (no status bar)
android.fullscreen = 1

# (str) Orientation of the app (portrait/landscape/behind/sensor)
android.orientation = portrait

# (list) Android specific features
#android.manifest.features = android.hardware.usb.host

# (list) Android specific libraries
#android.libraries =

# (str) Android logcat filter
#android.logcat_filters = *:S python:V

# (bool) By default, python-for-android copies the libs to the apk
#android.copy_libs = True

# (str) Android entry point (default: org.kivy.android.PythonActivity)
#android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app theme
#android.theme = @android:style/Theme.NoTitleBar

# (str) Java source to compile
#android.gradle_src_dir =

# (str) Add Java files to the APK
#android.add_src =

# (str) Python for android distribution name
#p4a.distribution_name = aql_inspector

# (str) Requirements
requirements = python3,kivy==2.3.1,hostpython3

# (str) Log level for the build process
log_level = 2

# (bool) Prepend a script to the python app (useful for importing)
#android.add_src =

# (str) Extra Java compile args
#android.add_compile_args =

# (bool) Try to use the ARM64 architecture only, reducing APK size
android.archs = arm64-v8a

# (str) Supported architectures (arm64-v8a, armeabi-v7a)
#android.arch = arm64-v8a

# (str) Android Google Services (JSON file)
#android.gradle_dependencies =

# (str) Files to add to the APK
#android.add_src =

# (str) Extra libraries to include
#android.add_libs =

# (str) Extra Java classes to include
#android.add_aars =

[buildozer]

# (int) Log level (0=error, 1=info, 2=debug)
log_level = 2

# (str) Path to the build directory
warn_on_root = 0

# (str) Path to the Android SDK
#android.sdk_path =

# (str) P4A directory (local python-for-android fork)
#p4a.local_dir =

# (str) P4A branch to use
#p4a.branch = develop
