#export WORK_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export REPO_ROOT=$(git rev-parse --show-toplevel)
export GIT_SSL_NO_VERIFY=1

#-------------------------------------------
# create virtual env
#-------------------------------------------
if [ ! -z $VIRTUAL_ENV ]; then
    echo "deactivate ENV $(basename $VIRTUAL_ENV)"
    deactivate
fi

virtual_folder="${REPO_ROOT}/.venv"

echo "virtual folder: $virtual_folder"
if [  ! -d $virtual_folder ]; then
    pushd .
    cd ${REPO_ROOT}
    echo "Warning: virtual env not setup."
    echo "creating virtual env folder $virtual_folder"
    virtualenv --always-copy --python=python3 $virtual_folder
    . $virtual_folder/bin/activate
    pip install -r ${REPO_ROOT}/requirements.txt
    popd
else
    . $virtual_folder/bin/activate
    #pip3 install -U --process-dependency-links -r requirements.txt

fi
export PYTHONPATH=.
echo ""
echo "+OK. in virtual environment $virtual_folder"
echo "Please enter 'deactivated' to get out of virtual envirnoment"
