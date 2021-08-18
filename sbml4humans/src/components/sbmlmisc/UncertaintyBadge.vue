<template>
    <div class="product-item">
        <div class="image-container">
            <img :src="'demo/images/product/' + slotProps.item.image" :alt="slotProps.item.name" />
        </div>
        <div class="product-list-detail">
            <h6 class="p-mb-2">{{slotProps.item.name}}</h6>
            <i class="pi pi-tag product-category-icon"></i>
            <span class="product-category">{{slotProps.item.category}}</span>
        </div>
        <div class="product-list-action">
            <h6 class="p-mb-2">${{slotProps.item.price}}</h6>
            <span :class="'product-badge status-'+slotProps.item.inventoryStatus.toLowerCase()">{{slotProps.item.inventoryStatus}}</span>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import additionalInfoUtils from "@/helpers/additionalInfoUtils";

export default defineComponent({
    props: {
        qualifier: {
            type: String,
            default: "",
        },
        resource: {
            type: String,
            default: "",
        },
    },

    data() {
        return {
            addInfo: {},
        };
    },

    created() {
        const parts = this.resource.split("/");
        const resourceID = parts[parts.length - 1];
        additionalInfoUtils.fetchAdditionalInfo(resourceID).then((res) => {
            console.log(res);
            this.addInfo = res as Record<string, unknown>;
        });
    },
});
</script>

<style lang="scss" scoped>
.qualifier {
    border-radius: 5px 0 0 5px;
}

.resource {
    border-radius: 0px 5px 5px 0;
}
</style>
