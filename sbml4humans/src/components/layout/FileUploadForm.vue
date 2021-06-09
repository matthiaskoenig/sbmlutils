<template>
    <div class="container">
        <form class="needs-validation" @submit.prevent="submitForm">
            <h5>Upload an SBML file to generate report</h5>
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
                    <label for="validationTooltip05">Math Rendering Format</label>
                    <select
                        ref="math"
                        class="custom-select"
                        id="validationTooltip05"
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
            <button class="btn btn-info w-25" type="submit" style="border-radius: 25px">Submit</button>
        </form>
        <div class="loader" v-if="loading">
            <h6>Please wait...</h6>
            <span class="loading"><a-spin size="large" /></span>
        </div>
    </div>
</template>

<script>
import store from "@/store/index";

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

            const headers = {
                "Content-Type": "multipart/form-data",
            };

            var payload = {
                formData: formData,
                headers: headers,
            };

            console.log("here at 99");
            store.dispatch("fetchReport", payload);
        },
    },

    computed: {
        loading() {
            return store.state.fileLoading;
        },
    }
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/FileUpload.scss";
</style>
