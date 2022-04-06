<template>
    <div class="p-mx-2">
        <TabView class="p-mx-2 p-my-4">
            <TabPanel>
                <template #header>
                    <i class="pi pi-file p-mr-2"></i>
                    <span>Upload File</span>
                </template>
                <FileUploadForm />
            </TabPanel>
            <TabPanel>
                <template #header>
                    <i class="pi pi-link p-mr-2"></i>
                    <span>Submit URL</span>
                </template>
                <URLUpload />
            </TabPanel>
            <TabPanel>
                <template #header>
                    <i class="pi pi-copy p-mr-2"></i>
                    <span>Paste SBML</span>
                </template>
                <PasteSBML />
            </TabPanel>
        </TabView>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

import FileUploadForm from "@/components/layout/FileUploadForm.vue";
import URLUpload from "@/components/layout/URLUpload.vue";
import PasteSBML from "@/components/layout/PasteSBML.vue";

export default defineComponent({
    components: {
        FileUploadForm,
        URLUpload,
        PasteSBML,
    },
});
</script>

<style>
/*.tabs {
    border-bottom: 1px solid lightgrey;
    border-left: 1px solid lightgrey;
    border-right: 1px solid lightgrey;
    border-radius: 0 0 5px 5px;
}*/

.p-tabview {
    padding: 0 !important;
    margin: 0 !important;
}

.p-tabview-nav-link:focus {
    outline: none !important;
    box-shadow: none !important;
}

.p-tabview-panels {
    border-bottom: 1px solid lightgrey !important;
    border-left: 1px solid lightgrey !important;
    border-right: 1px solid lightgrey !important;
    border-radius: 0 5px 5px 5px !important;
}
</style>
