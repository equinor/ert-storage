
copy_test_files () {
    cp -r $CI_SOURCE_ROOT/tests $CI_TEST_ROOT/tests
}

install_test_dependencies () {
    pip install .[test]
}

install_package () {
    pip install . --no-deps
}

start_tests () {
    pytest -k "not test_typing"
}
