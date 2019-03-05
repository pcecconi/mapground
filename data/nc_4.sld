<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:se="http://www.opengis.net/se" xmlns:ogc="http://www.opengis.net/ogc" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
    <NamedLayer>
        <se:Name>default</se:Name>
        <UserStyle>
            <se:Name>//CMI</se:Name>
            <se:FeatureTypeStyle>
                <se:Rule>
                    <se:RasterSymbolizer>
                        <se:Geometry>
                            <ogc:PropertyName>tito</ogc:PropertyName>
                        </se:Geometry>
                        <se:Opacity>1</se:Opacity>
                        <se:ColorMap>
                            <se:ColorMapEntry color="#d7191c" label="-1.000000" opacity="1.0" quantity="-1"/>
                            <se:ColorMapEntry color="#fdae61" label="234.668000" opacity="1.0" quantity="234.668"/>
                            <se:ColorMapEntry color="#ffffbf" label="470.336000" opacity="1.0" quantity="470.336"/>
                            <se:ColorMapEntry color="#abdda4" label="706.004000" opacity="1.0" quantity="706.004"/>
                            <se:ColorMapEntry color="#2b83ba" label="941.672000" opacity="1.0" quantity="941.672"/>
                        </se:ColorMap>
                    </se:RasterSymbolizer>
                </se:Rule>
            </se:FeatureTypeStyle>
        </UserStyle>
    </NamedLayer>
</StyledLayerDescriptor>

