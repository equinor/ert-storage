
copy_test_files () {
    cp -r $CI_SOURCE_ROOT/tests $CI_TEST_ROOT/tests
}

install_test_dependencies () {
    pip install black pytest
}

install_package () {
    pip install . --no-deps
}

start_tests () {
    run_spe1_tests
    test_result=$?
    if [ "$test_result" -gt 0 ];
    then
        exit $test_result
    fi
    pytest -vs -k "not spe1"
}

run_spe1_tests() {
  pushd tests/data/spe1_st

  echo "Initiating Ert run for Spe1 with new storage enabled..."
  ert ensemble_experiment --enable-new-storage spe1.ert
  echo "Ert run finished"

  echo "Test for accessing Spe1 data ..."
  pytest ../../../ -vs -k spe1

  popd
}
