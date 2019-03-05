<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:se="http://www.opengis.net/se" xmlns:ogc="http://www.opengis.net/ogc" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <se:Name>wrfprs_d01</se:Name>
    <UserStyle>
      <se:Name>Temperatura</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:RasterSymbolizer>
            <se:Geometry>
              <ogc:PropertyName>grid</ogc:PropertyName>
            </se:Geometry>
            <se:Opacity>1</se:Opacity>
              <se:ColorMap>
                            <se:ColorMapEntry color="#380083" label="-18" opacity="1.0" quantity="-18"/>
                            <se:ColorMapEntry color="#480093" label="-16" opacity="1.0" quantity="-16"/>
                            <se:ColorMapEntry color="#09147f" label="-14" opacity="1.0" quantity="-14"/>
                            <se:ColorMapEntry color="#122899" label="-12" opacity="1.0" quantity="-12"/>
                            <se:ColorMapEntry color="#1b3db2" label="-10" opacity="1.0" quantity="-10"/>
                            <se:ColorMapEntry color="#2451cc" label="-8" opacity="1.0" quantity="-8"/>
                            <se:ColorMapEntry color="#2d65e5" label="-6" opacity="1.0" quantity="-6"/>
                            <se:ColorMapEntry color="#367aff" label="-4" opacity="1.0" quantity="-4"/>
                            <se:ColorMapEntry color="#498dff" label="-2" opacity="1.0" quantity="-2"/>
                            <se:ColorMapEntry color="#5ca0ff" label="0" opacity="1.0" quantity="0"/>
                            <se:ColorMapEntry color="#70b4ff" label="2" opacity="1.0" quantity="2"/>
                            <se:ColorMapEntry color="#83c7ff" label="4" opacity="1.0" quantity="4"/>
                            <se:ColorMapEntry color="#96daff" label="6" opacity="1.0" quantity="6"/>
                            <se:ColorMapEntry color="#aaeeff" label="8" opacity="1.0" quantity="8"/>
                            <se:ColorMapEntry color="#c6f3ff" label="10" opacity="1.0" quantity="10"/>
                            <se:ColorMapEntry color="#90e8aa" label="12" opacity="1.0" quantity="12"/>
                            <se:ColorMapEntry color="#a0fc85" label="14" opacity="1.0" quantity="14"/>
                            <se:ColorMapEntry color="#cfff78" label="16" opacity="1.0" quantity="16"/>
                            <se:ColorMapEntry color="#e5f088" label="18" opacity="1.0" quantity="18"/>
                            <se:ColorMapEntry color="#fce198" label="20" opacity="1.0" quantity="20"/>
                            <se:ColorMapEntry color="#f8ca5b" label="22" opacity="1.0" quantity="22"/>
                            <se:ColorMapEntry color="#fbb260" label="24" opacity="1.0" quantity="24"/>
                            <se:ColorMapEntry color="#fd9657" label="26" opacity="1.0" quantity="26"/>
                            <se:ColorMapEntry color="#ff7b36" label="28" opacity="1.0" quantity="28"/>
                            <se:ColorMapEntry color="#ff5c29" label="30" opacity="1.0" quantity="30"/>
                            <se:ColorMapEntry color="#ff3d1b" label="32" opacity="1.0" quantity="32"/>
                            <se:ColorMapEntry color="#e60000" label="34" opacity="1.0" quantity="34"/>
                            <se:ColorMapEntry color="#c00000" label="36" opacity="1.0" quantity="36"/>
                            <se:ColorMapEntry color="#9a0000" label="38" opacity="1.0" quantity="38"/>
                            <se:ColorMapEntry color="#730000" label="40" opacity="1.0" quantity="40"/>
                            <se:ColorMapEntry color="#4d0000" label="42" opacity="1.0" quantity="42"/>
                <se:ColorMapEntry color="#f9f9f9" label="&gt;42" opacity="1.0" quantity="inf"/>
              </se:ColorMap>
          </se:RasterSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
