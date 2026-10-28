# Disposable fixture-only project mutation, never a consumer migration helper.
require 'pathname'
abort 'Expected PROJECT SOURCE [--check]' unless [2, 3].include?(ARGV.length) && (ARGV.length == 2 || ARGV[2] == '--check')
selected_root=Pathname.new(__dir__).realpath.parent.parent.parent
project_path=Pathname.new(ARGV.fetch(0)).realpath
source=Pathname.new(ARGV.fetch(1)).realpath
expected_project=selected_root.join('output/mobile-ui-workflow/runtime/ios/OrbynWorkflowFixture.xcodeproj')
expected_source=selected_root.join('tests/fixtures/mobile-ui-workflow/native-ui-tests.swift')
abort 'Expected exact owned fixture project and source' unless project_path == expected_project && project_path.directory? && source == expected_source && source.file?
if ARGV[2] == '--check'
 puts 'Owned fixture paths validated; no project opened or written'
 exit 0
end
require 'xcodeproj'
project=Xcodeproj::Project.open(project_path)
abort 'Test target already exists' if project.targets.any? { |t| t.name=='NativeWorkflowTests' }
app=project.targets.find { |t| t.name=='OrbynWorkflowFixture' } or abort 'Missing app'
target=project.new_target(:ui_test_bundle,'NativeWorkflowTests',:ios,'16.0')
target.add_dependency(app)
target.source_build_phase.add_file_reference(project.main_group.new_file(source.to_s))
target.build_configurations.each do |config|
 config.build_settings['PRODUCT_BUNDLE_IDENTIFIER']='dev.orbyn.workflowfixture.uitests'
 config.build_settings['TEST_TARGET_NAME']='OrbynWorkflowFixture'
 config.build_settings['SWIFT_VERSION']='6.0'
 config.build_settings['PRODUCT_NAME']='$(TARGET_NAME)'
 config.build_settings['ONLY_ACTIVE_ARCH']='YES'
 config.build_settings['GENERATE_INFOPLIST_FILE']='YES'
 config.build_settings['CODE_SIGNING_ALLOWED']='NO'
end
project.save
scheme_path=project_path.join('xcshareddata/xcschemes/OrbynWorkflowFixture.xcscheme')
scheme=Xcodeproj::XCScheme.new(scheme_path)
scheme.add_test_target(target)
scheme.save_as(project_path,'OrbynWorkflowFixture',true)
puts 'Configured owned NativeWorkflowTests target'
