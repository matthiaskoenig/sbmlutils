<template>
    <div class="container">
        <img alt="SBML logo" src="@/assets/images/logo.png" />
        <form class="needs-validation" @submit.prevent="submitForm()">
            <legend>Upload an SBML file to generate report</legend>
            <div class="form-row">
                <div class="col-md-12 mb-3">
                    <label for="fileField">File</label>
                    <input
                        type="file"
                        ref="file"
                        id="fileField"
                        class="form-control"
                        v-on:change="handleFileUpload()"
                        required
                    />
                    <div class="invalid-tooltip">Please upload a valid SBML File.</div>
                </div>
            </div>
            <div class="form-row">
                <div class="col-md-6 mb-6">
                    <label for="validationTooltip04">File Format</label>
                    <select
                        ref="format"
                        class="custom-select"
                        id="validationTooltip04"
                        required
                    >
                        <option selected value="sbml">SBML File</option>
                        <option value="combine">COMBINE Archive</option>
                    </select>
                    <div class="invalid-tooltip">
                        Please select a valid math rendering format.
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="validationTooltip04">Math Rendering Format</label>
                    <select
                        ref="math"
                        class="custom-select"
                        id="validationTooltip04"
                        required
                    >
                        <option selected value="latex">LaTex</option>
                        <option value="cmathml">CMathML</option>
                        <option value="pmathml">PMathML</option>
                    </select>
                    <div class="invalid-tooltip">
                        Please select a valid math rendering format.
                    </div>
                </div>
            </div>
            <button class="btn btn-primary">Submit form</button>
        </form>
    </div>
</template>

<script>
import axios from "axios";

import API_BASE_URL from "@/data/urls";

export default {
    data() {
        return {
            file: null,
            mathRender: "latex",
            fileFormat: "sbml",
        };
    },

    methods: {
        // eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
        handleFileUpload() {
            this.file = this.$refs.file.files[0]; // add latest file in FileList to file attribute of component
        },

        async submitForm() {
            this.mathRender = this.$refs.math.value;
            this.fileFormat = this.$refs.format.value;

            let formData = new FormData();
            formData.append("source", this.file);

            formData.append("math", this.mathRender);
            formData.append("format", this.fileFormat);

            const url = API_BASE_URL + "/sbml";
            const res = await axios.post(url, formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });

            if (res.status === 200 && !res.data.error) {
                alert("SUCCESS: " + res.data.debug.json_report_time + " seconds");
            } else if (res.data.error) {
                alert("ERROR: " + res.data.error);
            } else {
                alert("FAILURE");
            }
        },
    },
};
</script>

<style lang="scss" scoped>
@import "../assets/styles/scss/components/FileUpload.scss";
</style>
