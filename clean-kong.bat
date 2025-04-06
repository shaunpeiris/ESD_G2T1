@echo off
echo 🧹 Deleting existing routes...

powershell -NoProfile -Command ^
"try { ^
    $routes = Invoke-RestMethod http://localhost:8001/routes; ^
    foreach ($r in $routes.data) { ^
        Write-Host '🔻 Deleting route ID:' $r.id; ^
        Invoke-RestMethod -Method DELETE http://localhost:8001/routes/$($r.id); ^
    } ^
} catch { Write-Host '⚠️ Failed to fetch/delete routes:' $_ }"

echo.
echo 🧹 Deleting existing services...

powershell -NoProfile -Command ^
"try { ^
    $services = Invoke-RestMethod http://localhost:8001/services; ^
    foreach ($s in $services.data) { ^
        Write-Host '🔻 Deleting service ID:' $s.id; ^
        Invoke-RestMethod -Method DELETE http://localhost:8001/services/$($s.id); ^
    } ^
} catch { Write-Host '⚠️ Failed to fetch/delete services:' $_ }"

echo.
echo ✅ Cleanup done
