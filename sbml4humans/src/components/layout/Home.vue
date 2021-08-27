<template>
    <div>
        <div class="p-grid">
            <div class="p-col-12 p-lg-6">
                <div>
                    <!-- <file-upload-form /> -->
                    <div class="p-m-3">
                        <submit-options />
                    </div>
                    <div class="p-m-3">
                        <about />
                    </div>
                </div>
            </div>
            <div class="p-col-12 p-lg-6">
                <div class="p-m-3">
                    <examples />
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

import Examples from "@/components/layout/Examples.vue";
import FileUploadForm from "@/components/layout/FileUploadForm.vue";
import About from "@/components/layout/About.vue";
import SubmitOptions from "@/components/layout/SubmitOptions.vue";

/**
 * Component to display the components to appear on the landing page.
 *      - SBML File upload
 *      - List of Examples
 *      - About Info
 */
export default defineComponent({
    components: {
        Examples,
        //FileUploadForm,
        SubmitOptions,
        About,
    },
});
</script>

<style scoped lang="scss"></style>
