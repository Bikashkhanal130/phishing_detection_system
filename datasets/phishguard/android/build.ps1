# PowerShell helper to build the PhishGuard Android app using Android Studio's
# bundled JDK and the locally-cached Gradle 8.10.2.
$ErrorActionPreference = 'Stop'

$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = "C:\Users\Bikash\AppData\Local\Android\Sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

$gradleBin = "C:\Users\Bikash\.gradle\wrapper\dists\gradle-8.10.2-bin\a04bxjujx95o3nb99gddekhwo\gradle-8.10.2\bin\gradle.bat"

# Forward all CLI args to gradle (e.g., assembleDebug, build, tasks).
& $gradleBin @args
exit $LASTEXITCODE
