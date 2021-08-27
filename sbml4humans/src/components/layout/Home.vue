<template>
    <div>
        <div class="p-grid">
            <div class="p-col-12 p-lg-6">
                <div>
                    <!-- <file-upload-form /> -->
                    <div class="p-m-3">
                        <submit-options/>
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
import SubmitOptions from "@/components/layout/SubmitOptions.vue";


export default defineComponent({
    components: {
        Examples,
        SubmitOptions,
    },
});
</script>

<style scoped lang="scss"></style>
