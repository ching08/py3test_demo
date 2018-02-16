export WORK_HOME=$(git rev-parse --show-toplevel)
if [ "${WORK_HOME}x" == "x"  ]; then
    export WORK_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

export GIT_SSL_NO_VERIFY=1



#-------------------------------------------
# create virtual env
#-------------------------------------------
if [ ! -z $VIRTUAL_ENV ]; then
    echo "deactivate ENV $(basename $VIRTUAL_ENV)"
    deactivate
fi

virtual_folder="${WORK_HOME}/.venv"

echo "virtual folder: $virtual_folder"
if [  ! -d $virtual_folder ]; then
    pushd .
    cd ${WORK_HOME}
    echo "Warning: virtual env not setup."
    echo "creating virtual env folder $virtual_folder"
    virtualenv --always-copy --python=python3 $virtual_folder
    . $virtual_folder/bin/activate
    if [ -f ${WORK_HOME}/requirements.txt ] ; then
	pip install -r ${WORK_HOME}/requirements.txt
    fi
    popd
else
    . $virtual_folder/bin/activate
    #pip3 install -U --process-dependency-links -r requirements.txt

fi
export PYTHONPATH=.
echo ""
echo "+OK. in virtual environment $virtual_folder"
echo "Please enter 'deactivated' to get out of virtual envirnoment"

