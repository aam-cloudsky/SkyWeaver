<template>

  <div class="layer-tree">

    <h2>Layers</h2>

    <label>
      <input type="checkbox" checked />
      Droneports
    </label>

    <label>
      <input type="checkbox" checked />
      Routes
    </label>

    <label>
      <input type="checkbox" checked />
      Restrictions
    </label>

    <label>
      <input type="checkbox" checked />
      HexGrid
    </label>

    <label>
      <input type="checkbox" checked />
      Air Corridors
    </label>

    <label>
      <input type="checkbox" checked />
      Reachability
    </label>

  </div>

</template>

<style scoped>

.layer-tree {
  display: flex;
  flex-direction: column;

  gap: 10px;
}

label {
  display: flex;
  align-items: center;

  gap: 8px;

  cursor: pointer;
}

</style>