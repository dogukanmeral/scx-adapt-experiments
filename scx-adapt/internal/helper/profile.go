package helper

import (
	"fmt"
	"internal/checks"
	"os"
	"regexp"
	"sort"

	"github.com/go-playground/validator/v10"
	"gopkg.in/yaml.v3"
)

type Config struct {
	Interval   int         `yaml:"internal" validate:"required,gte=1"` // ms
	Schedulers []Scheduler `yaml:"schedulers" validate:"required,dive"`
}

type Scheduler struct {
	Path      string     `yaml:"path" validate:"required"`
	Priority  int        `yaml:"priority" validate:"required,gte=1,lte=139"`
	Criterias []Criteria `yaml:"criterias" validate:"required,dive"`
}

// Interface for sorting schedulers by their priority
func (c Config) Len() int {
	return len(c.Schedulers)
}

func (c Config) Less(i, j int) bool {
	return c.Schedulers[i].Priority < c.Schedulers[j].Priority
}

func (c Config) Swap(i, j int) {
	c.Schedulers[i], c.Schedulers[j] = c.Schedulers[j], c.Schedulers[i]
}

/*
	Valid value_name(s):
		(cpu|io|mem)_psi_(some|full)_(10|60|300)
		load_avg_(1|5|15)
		procs_running
		procs_blocked
		procs_disk_io
*/

var VALID_VALUE_REGEX = [...]string{
	"^(cpu|io|mem)_psi_(some|full)_(10|60|300)$",
	"^load_avg_(1|5|15)$",
	"^procs_running$",
	"^procs_blocked$",
	"^procs_disk_io$",
}

type Criteria struct {
	ValueName string   `yaml:"value_name" validate:"required"`
	MoreThan  *float64 `yaml:"more_than"`
	LessThan  *float64 `yaml:"less_than"`
}

func (c Criteria) Validate() error {
	v := validator.New()

	if err := v.Struct(c); err != nil {
		return err
	}

	for _, r := range VALID_VALUE_REGEX {
		if m, _ := regexp.MatchString(r, c.ValueName); m {
			goto valueNameValid
		}
	}
	return fmt.Errorf("Invalid value_name: %s\n", c.ValueName)

valueNameValid:

	if c.MoreThan == nil && c.LessThan == nil {
		return fmt.Errorf("There is no 'more_than' and/or 'less_than' parameter for value '%s'\n", c.ValueName)
	}

	if c.MoreThan != nil && c.LessThan != nil {
		if *c.MoreThan >= *c.LessThan {
			return fmt.Errorf("Parameter 'more_than' cannot be >= 'less_than' in value '%s'\n", c.ValueName)
		}
	}

	return nil
}

func (s Scheduler) Validate() error {
	v := validator.New()

	if err := v.Struct(s); err != nil {
		return err
	}

	// Check if file at the path exists and a BPF object file
	if err := checks.CheckObj(s.Path); err != nil {
		return err
	}

	// Check all criterias inside scheduler
	var valueNames []string
	for _, c := range s.Criterias {
		valueNames = append(valueNames, c.ValueName)

		if err := c.Validate(); err != nil {
			return fmt.Errorf("Invalid criteria '%s': %s", c.ValueName, err)
		}
	}

	// Check if a criteria is defined multiple times in same scheduler
	cont, dup := checks.ContainsDuplicate(valueNames)
	if cont {
		return fmt.Errorf("Criteria(s) '%s' defined multiple times for scheduler '%s'\n", dup, s.Path)
	}

	return nil
}

func (conf Config) Validate() error {
	var priorities []int

	// Check all schedulers in config
	for _, s := range conf.Schedulers {
		priorities = append(priorities, s.Priority)

		if err := s.Validate(); err != nil {
			return fmt.Errorf("Error in scheduler '%s': %w", s.Path, err)
		}
	}

	// Check if a priority is assigned to multiple schedulers
	cont, dup := checks.ContainsDuplicate(priorities)
	if cont {
		return fmt.Errorf("Priority(s) '%d' is/are assigned for multiple schedulers\n", dup)
	}

	return nil
}

func ValidateYAML(yamlData []byte) error {
	conf, err := YamlConvert(yamlData)
	if err != nil {
		return err
	}

	if err := conf.Validate(); err != nil {
		return fmt.Errorf("Invalid config: %w", err)
	}

	return nil
}

func YamlConvert(data []byte) (Config, error) {
	var conf Config
	if err := yaml.Unmarshal(data, &conf); err != nil {
		return conf, err
	}

	return conf, nil
}

func RunProfile(profilePath string) error { // TODO: add /etc/scx-adapt and cwd stuff to cmd part, helpers just get absolute paths
	profileData, err := os.ReadFile(profilePath)
	if err != nil {
		return fmt.Errorf("Error occured while reading file '%s': %s\n", profilePath, err)
	}

	if err := ValidateYAML(profileData); err != nil {
		return err
	}

	conf, err := YamlConvert(profileData)
	if err != nil {
		return err
	}

	sort.Sort(conf) // Sort schedulers by their priority (smaller int has higher priority)

	// TODO: iterate over schedulers here (considering interval), add helpers for value checking
}
