/*
Copyright © 2026 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"internal/helper"
	"os"

	"github.com/spf13/cobra"
)

// removeCmd represents the remove command
var removeCmd = &cobra.Command{
	Use:   "remove-scheduler",
	Short: "Remove scheduler(s) from scx-adapt",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 0 {
			for _, scx := range args {
				err := helper.RemoveAddedScx(scx, "/var/lib/scx-adapt/obj")
				if err != nil {
					fmt.Println(err)
					os.Exit(1)
				}
				fmt.Printf("Scheduler removed: %s\n", scx)
			}
		} else {
			fmt.Println("Missing scheduler(s) as argument. scx-adapt --help to see usage")
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(removeCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// removeCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// removeCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
