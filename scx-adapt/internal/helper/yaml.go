package helper

import (
	"bytes"
	"fmt"
	"internal/checks"
	"regexp"

	"github.com/go-playground/validator/v10"
	"gopkg.in/yaml.v3"
)

/*
	Valid value_name(s):
		(cpu|io|mem)_psi_(some|full)_(10|60|300)
		load_avg_(1|5|15)
		procs_running
		procs_blocked
		procs_disk_io
*/

var VALID_VALUE_REGEX = map[string]string{
	"pressures":    "^(cpu|io|mem)_psi_(some|full)_(10|60|300)$",
	"loadAvgs":     "^load_avg_(1|5|15)$",
	"procsRunning": "^procs_running$",
	"procsBlocked": "^procs_blocked$",
	"procsDiskIo":  "^procs_disk_io$",
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

type Config struct {
	Interval   int         `yaml:"interval" validate:"required,gte=1"` // ms
	Schedulers []Scheduler `yaml:"schedulers" validate:"required,dive"`
}

type Scheduler struct {
	Path      string     `yaml:"path" validate:"required"`
	Priority  int        `yaml:"priority" validate:"required,gte=1,lte=139"`
	Criterias []Criteria `yaml:"criterias" validate:"required,dive"`
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
	v := validator.New()

	if err := v.Struct(conf); err != nil {
		return err
	}

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

func YamlToConfig(yamlData []byte) (Config, error) {
	var conf Config

	decoder := yaml.NewDecoder(bytes.NewReader(yamlData))
	decoder.KnownFields(true) // Check unrelated keys in YAML

	if err := decoder.Decode(&conf); err != nil {
		return conf, err
	}

	if err := conf.Validate(); err != nil {
		return conf, fmt.Errorf("Invalid configuration: %w", err)
	}

	return conf, nil
}
