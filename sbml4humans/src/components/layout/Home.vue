<template>
    <div>
        <div class="p-grid">
            <div class="p-col-12 p-lg-6">
                <div class="p-mx-5">
                    <file-upload-form/>
                    <examples/>
                </div>
            </div>
            <div class="p-col-12 p-lg-6">
                <div class="p-mx-5">
                    <about/>
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

/**
 * Component to display the components to appear on the landing page.
 *      - SBML File upload
 *      - List of Examples
 *      - About Info
 */
export default defineComponent({
    components: {
        Examples,
        FileUploadForm,
        About,
    },
});
</script>

<style scoped lang="scss"></style>
