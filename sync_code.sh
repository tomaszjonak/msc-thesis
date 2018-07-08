rsync -avz implementacja msc-remote: --exclude client_storage --exclude compression_analysis --exclude server_storage --exclude state_storage --exclude __pycache__ --exclude tests --exclude .git --exclude .cache --exclude filesystem_analysis --exclude integration_tests
ssh -A msc-remote 'rsync -avz implementacja/ gardawice:sender/'
ssh -A msc-remote 'rsync -avz implementacja/ mint:receiver/'
