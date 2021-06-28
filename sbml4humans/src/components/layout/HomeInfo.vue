<template>
    <div class="divider">
        <div class="left-container">
            <div class="file-upload">
                <upload-sbml></upload-sbml>
            </div>
            <div class="about">
                <examples-list></examples-list>
            </div>
        </div>
        <div class="right-container">
            <about></about>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

/* Components */
import ExamplesListContainer from "@/components/layout/ExamplesListContainer.vue";
import FileUploadForm from "@/components/layout/FileUploadForm.vue";
import About from "@/components/layout/About.vue";

/**
 * Component to display the components to appear on the landing page.
 *      - SBML File upload
 *      - List of Examples
 *      - About Info
 */
export default defineComponent({
    components: {
        "examples-list": ExamplesListContainer,
        "upload-sbml": FileUploadForm,
        about: About,
    },
});
</script>

<style scoped lang="scss">
@import "@/assets/styles/scss/components/layout/HomeInfo.scss";
</style>
